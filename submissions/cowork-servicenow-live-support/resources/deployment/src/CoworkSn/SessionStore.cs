using System.Text.Json;
using Microsoft.Data.Sqlite;

namespace CoworkSn;

/// <summary>
/// Single deployed instance only. Bounded striped locks serialize each session; SQLite transactions
/// atomically commit state, sequenced events and idempotency keys. No lock is held across HTTP.
/// Pending/ambiguous open or send operations are NEVER automatically replayed after restart.
/// A bridge administrator must reconcile their client_session_id/client_message_id in ServiceNow.
/// close_chat is the sole retryable mutation and always reuses its durable idempotency key.
/// </summary>
public sealed class SessionStore
{
    private readonly string _connectionString;
    private readonly object[] _locks = Enumerable.Range(0, 128).Select(_ => new object()).ToArray();
    private object LockFor(string key) => _locks[(uint)StringComparer.Ordinal.GetHashCode(key) % _locks.Length];

    public SessionStore(BridgeOptions options, IHostEnvironment environment)
    {
        var path = Path.GetFullPath(options.Storage.DatabasePath, environment.ContentRootPath);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        _connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = path, ForeignKeys = true, DefaultTimeout = 15, Pooling = false
        }.ToString();
        using var db = Open();
        using var command = db.CreateCommand();
        command.CommandText = """
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=FULL;
            CREATE TABLE IF NOT EXISTS sessions(
                id TEXT PRIMARY KEY, tenant TEXT NOT NULL, user_id TEXT NOT NULL, request_id TEXT NOT NULL,
                payload TEXT NOT NULL, terminal_at TEXT,
                UNIQUE(tenant,user_id,request_id));
            CREATE TABLE IF NOT EXISTS events(
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                sequence INTEGER NOT NULL, id TEXT NOT NULL UNIQUE, payload TEXT NOT NULL,
                PRIMARY KEY(session_id,sequence));
            CREATE TABLE IF NOT EXISTS operations(
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                key TEXT NOT NULL, fingerprint TEXT NOT NULL, state TEXT NOT NULL,
                PRIMARY KEY(session_id,key));
            CREATE TABLE IF NOT EXISTS callbacks(
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                key TEXT NOT NULL, PRIMARY KEY(session_id,key));
            """;
        command.ExecuteNonQuery();
    }

    private SqliteConnection Open()
    {
        var db = new SqliteConnection(_connectionString);
        db.Open();
        return db;
    }

    public ChatSession CreateDraft(Owner owner, string requestId, string summary, string? originalText, string? language, DateTimeOffset now)
    {
        lock (LockFor(owner.TenantId + owner.UserId + requestId))
        {
            using var db = Open();
            using var transaction = db.BeginTransaction();
            using var find = Command(db, transaction,
                "SELECT payload FROM sessions WHERE tenant=$tenant AND user_id=$user AND request_id=$request",
                ("$tenant", owner.TenantId), ("$user", owner.UserId), ("$request", requestId));
            if (find.ExecuteScalar() is string existing)
            {
                var session = JsonSerializer.Deserialize<ChatSession>(existing, ChatJson.Options)!;
                if (session.InitialSummary != summary || session.OriginalText != originalText || session.Language != language)
                    throw new ChatException("idempotency_conflict", "requestId was already used for different draft content.", 409);
                return session;
            }
            var created = new ChatSession
            {
                TenantId = owner.TenantId, UserId = owner.UserId, Email = owner.Email,
                RequestId = requestId, Summary = summary, InitialSummary = summary,
                OriginalText = originalText, Language = language, CreatedAt = now, LastActivityAt = now
            };
            using var insert = Command(db, transaction,
                "INSERT INTO sessions(id,tenant,user_id,request_id,payload) VALUES($id,$tenant,$user,$request,$payload)",
                ("$id", created.Id), ("$tenant", owner.TenantId), ("$user", owner.UserId), ("$request", requestId),
                ("$payload", JsonSerializer.Serialize(created, ChatJson.Options)));
            insert.ExecuteNonQuery();
            transaction.Commit();
            return created;
        }
    }

    public T Update<T>(string sessionId, Owner? owner, Func<SessionTransaction, T> action)
    {
        Input.SessionId(sessionId);
        lock (LockFor(sessionId))
        {
            using var db = Open();
            using var transaction = db.BeginTransaction();
            using var get = Command(db, transaction, "SELECT payload FROM sessions WHERE id=$id", ("$id", sessionId));
            var json = get.ExecuteScalar() as string;
            if (json is null) throw new ChatException("not_found", "Session not found.", 404);
            var session = JsonSerializer.Deserialize<ChatSession>(json, ChatJson.Options)!;
            if (owner is not null && (session.TenantId != owner.TenantId || session.UserId != owner.UserId))
                throw new ChatException("not_found", "Session not found.", 404);
            var tx = new SessionTransaction(db, transaction, session);
            var result = action(tx);
            var payload = JsonSerializer.Serialize(session, ChatJson.Options);
            if (payload != json)
            {
                using var update = Command(db, transaction, "UPDATE sessions SET payload=$payload,terminal_at=$terminal WHERE id=$id",
                    ("$id", sessionId), ("$payload", payload), ("$terminal", session.TerminalAt?.ToString("O")));
                update.ExecuteNonQuery();
            }
            transaction.Commit();
            return result;
        }
    }

    public ChatView View(string id, Owner owner, long afterSequence = 0)
    {
        if (afterSequence < 0) throw new ChatException("invalid_argument", "afterSequence cannot be negative.");
        return Update(id, owner, tx =>
        {
            var s = tx.Session;
            if (afterSequence > s.Sequence) throw new ChatException("invalid_cursor", "afterSequence is beyond this session's event stream.");
            using var command = Command(tx.Database, tx.Transaction,
                "SELECT payload FROM events WHERE session_id=$id AND sequence>$after ORDER BY sequence LIMIT 5",
                ("$id", id), ("$after", afterSequence));
            using var reader = command.ExecuteReader();
            var events = new List<ChatEvent>();
            var cursor = afterSequence;
            while (reader.Read())
            {
                var item = JsonSerializer.Deserialize<ChatEvent>(reader.GetString(0), ChatJson.Options)!;
                events.Add(item);
                var candidate = new ChatView(id, s.Status, s.Summary, s.InteractionNumber, events, item.Sequence, item.Sequence < s.Sequence);
                if (JsonSerializer.SerializeToUtf8Bytes(candidate, ChatJson.Options).Length > 60 * 1024)
                {
                    events.RemoveAt(events.Count - 1);
                    break;
                }
                cursor = item.Sequence;
            }
            return new ChatView(id, s.Status, s.Summary, s.InteractionNumber, events, cursor, cursor < s.Sequence);
        });
    }

    public string[] ActiveIds()
    {
        using var db = Open();
        using var command = db.CreateCommand();
        command.CommandText = "SELECT id FROM sessions WHERE terminal_at IS NULL";
        using var reader = command.ExecuteReader();
        var ids = new List<string>();
        while (reader.Read()) ids.Add(reader.GetString(0));
        return ids.ToArray();
    }

    public void Cleanup(DateTimeOffset cutoff)
    {
        using var db = Open();
        using var command = db.CreateCommand();
        command.CommandText = """
            DELETE FROM sessions
            WHERE terminal_at IS NOT NULL AND terminal_at<$cutoff
              AND NOT EXISTS (
                  SELECT 1 FROM operations
                  WHERE operations.session_id=sessions.id
                    AND operations.key LIKE 'client:%'
                    AND operations.state IN ('pending','ambiguous'))
            """;
        command.Parameters.AddWithValue("$cutoff", cutoff.ToString("O"));
        command.ExecuteNonQuery();
    }

    internal static SqliteCommand Command(SqliteConnection db, SqliteTransaction transaction, string sql,
        params (string Name, object? Value)[] values)
    {
        var command = db.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = sql;
        foreach (var (name, value) in values) command.Parameters.AddWithValue(name, value ?? DBNull.Value);
        return command;
    }
}

public sealed class SessionTransaction(SqliteConnection database, SqliteTransaction transaction, ChatSession session)
{
    internal SqliteConnection Database { get; } = database;
    internal SqliteTransaction Transaction { get; } = transaction;
    public ChatSession Session { get; } = session;

    public void Append(string kind, string author, string text, DateTimeOffset now, string? originalText = null, string? language = null)
    {
        var item = new ChatEvent(Guid.NewGuid().ToString("N"), ++Session.Sequence, kind, author, text, now, originalText, language);
        using var command = SessionStore.Command(Database, Transaction,
            "INSERT INTO events(session_id,sequence,id,payload) VALUES($session,$sequence,$id,$payload)",
            ("$session", Session.Id), ("$sequence", item.Sequence), ("$id", item.Id),
            ("$payload", JsonSerializer.Serialize(item, ChatJson.Options)));
        command.ExecuteNonQuery();
    }

    public bool Reserve(string key, string fingerprint)
    {
        using var read = SessionStore.Command(Database, Transaction,
            "SELECT fingerprint FROM operations WHERE session_id=$id AND key=$key", ("$id", Session.Id), ("$key", key));
        if (read.ExecuteScalar() is string existing)
        {
            if (existing != fingerprint) throw new ChatException("idempotency_conflict", "This idempotency key was used for a different operation.", 409);
            return false;
        }
        using var insert = SessionStore.Command(Database, Transaction,
            "INSERT INTO operations(session_id,key,fingerprint,state) VALUES($id,$key,$fingerprint,'pending')",
            ("$id", Session.Id), ("$key", key), ("$fingerprint", fingerprint));
        insert.ExecuteNonQuery();
        return true;
    }

    public string? OperationState(string key)
    {
        using var read = SessionStore.Command(Database, Transaction,
            "SELECT state FROM operations WHERE session_id=$id AND key=$key", ("$id", Session.Id), ("$key", key));
        return read.ExecuteScalar() as string;
    }

    public void Mark(string key, string state)
    {
        using var update = SessionStore.Command(Database, Transaction,
            "UPDATE operations SET state=$state WHERE session_id=$id AND key=$key",
            ("$id", Session.Id), ("$key", key), ("$state", state));
        update.ExecuteNonQuery();
    }

    public bool RecordCallback(string key)
    {
        using var insert = SessionStore.Command(Database, Transaction,
            "INSERT OR IGNORE INTO callbacks(session_id,key) VALUES($id,$key)", ("$id", Session.Id), ("$key", key));
        return insert.ExecuteNonQuery() == 1;
    }

    public void Terminal(string status, string reason, DateTimeOffset now)
    {
        if (Session.Terminal) return;
        Session.Status = status;
        Session.TerminalAt = now;
        Append(status, "system", reason, now);
    }
}
