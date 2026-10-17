# Component catalog

Where each Power Platform component lives in an exported solution, how to identify it, what counts as a meaningful change, and what to ignore. Paths are relative to the root of the exported `.zip`. In `customizations.xml`, the root element is `ImportExportXml`; collection names are given as they appear there.

## Package-level files

| File | Content | Compare |
| --- | --- | --- |
| `solution.xml` | `SolutionManifest`: `UniqueName` (a patch is `<name>_Patch_<hex>`, an upgrade holding solution `<name>_Upgrade`), `LocalizedNames`, `Version`, `Managed` (0 unmanaged, 1 managed, 2 both), `Publisher` with `CustomizationPrefix`, `RootComponents` (component type code, schema name or ID, behavior 0 include subcomponents, 1 do not include, 2 shell only), `MissingDependencies` with `Required` and `Dependent` entries | Unique name and publisher must match for an import over the installed solution; version should increase; root components added or removed; new missing dependencies. Decode type codes with the table at the end of this file |
| `customizations.xml` | All component definitions except binaries and flow JSON | Collection by collection, below |
| `[Content_Types].xml` | Packaging metadata | Ignore |

## Dataverse schema

| Component | Location | Identifier | Meaningful change | Ignore |
| --- | --- | --- | --- | --- |
| Table | `Entities/Entity`, `Name` element (text is schema name), `EntityInfo/entity` | Schema name | Ownership, audit, activity, queue, change tracking, entity set name, display names, icons, primary name column, keys (`EntityKeys`), settings such as duplicate detection | `IntroducedVersion` |
| Column | `EntityInfo/entity/attributes/attribute` | `PhysicalName` attribute | `Type`, `RequiredLevel` (values `none`, `recommended`, `required`, `systemrequired`), `MaxLength` or `Length`, `Format`, precision and min/max, `IsSecured`, `IsAuditEnabled`, lookup targets, calculated or rollup formula, display name, description, local choice options | `IntroducedVersion`, autonumber seed |
| Relationship | `EntityRelationships/EntityRelationship` | `Name` attribute | Type (one-to-many, many-to-many), referencing and referenced tables, cascade behaviors (`CascadeDelete`, `CascadeAssign`, `CascadeShare`, etc.), relationship behavior, lookup column | Display names only |
| Global choice | `optionsets/optionset` | `Name` attribute | Option values added or removed, labels, external values, colors | Label ordering |
| Local choice | Inside the column: `attribute/optionset/options/option` | Column + `value` | Same as global choice | Same |
| Alternate key | `EntityInfo/entity/EntityKeys/EntityKey` (inside the table's entity element, so a table-level comparison includes it) | Logical name | Key columns | None |

## User interface

| Component | Location | Identifier | Meaningful change | Ignore |
| --- | --- | --- | --- | --- |
| Form | `Entities/Entity/FormXml/forms[@type]/systemform` | `formid`, with `LocalizedNames` label; the `forms` type attribute says main, quick create, quick view, card, etc. | Tabs, sections, controls and their `datafieldname`, required and visibility settings, event handlers and libraries, the order of tabs, sections, columns, rows, and cells, form order, activation state, security roles assigned to the form | GUID formatting, whitespace |
| View | `Entities/Entity/SavedQueries/savedqueries/savedquery` | `savedqueryid` | `fetchxml` (filter `type` and nesting, conditions, links and their `all-attributes` setting, sort attributes and sort order), `layoutxml` (columns, column order, widths), query type, default view. For cross-references, each column is attributed to its owning table: `link-entity` columns and join `from` columns to the linked table, join `to` columns to the parent, aliased conditions (wherever they appear in the query) and `alias.column` cells to the aliased table | Column width changes are cosmetic |
| Chart | `Entities/Entity/Visualizations/visualization` | `savedqueryvisualizationid` | Data and presentation description XML | None |
| Command bar | `Entities/Entity/RibbonDiffXml`; application ribbon in `AppRibbon` or `RibbonDiffXml` at root | Table | Custom actions, hide actions, rules, commands, JavaScript references | None |
| Dashboard | `Dashboards/Dashboard` | `FormId` with `LocalizedNames` | `FormXml` content, security roles | None |
| Sitemap | `SiteMaps/SiteMap` | `SiteMapUniqueName` | Areas, groups, subareas, entities, URLs, titles, privileges, and their order (navigation order is reported as a low-severity layout change) | None |
| Model-driven app | `AppModules/AppModule`; app sitemaps may also appear under `AppModuleSiteMaps` | `UniqueName` | `AppModuleComponents` (tables, forms, views, flows, dashboards; keyed by `schemaName` or `id`), navigation type, client type, descriptions, roles | Descriptions |
| Canvas app and custom page | `CanvasApps/CanvasApp`; the `DocumentUri`, `BackgroundImageUri`, and icon URI elements name the packaged files under `CanvasApps/`. The `.msapp` is a zip: apps carry `Controls/*.json` (one `TopParent` per screen with nested `Children` and `Rules` of `Property` and `InvariantScript`), component definitions under `Components/*.json` with names in `ComponentsMetadata.json`, or source as `Src/*.pa.yaml`; all carry `Properties.json` (`LocalConnectionReferences` and `LocalDatabaseReferences` as JSON strings) and `References/DataSources.json`; media under `Assets/` | `Name` element | Screens, components, and controls added, removed, renamed, or reordered within their parent (layout order in auto-layout containers, z-order elsewhere); property formulas and container layout formulas (`DynamicProperties`) changed; component custom-property definitions; group membership; connections (keyed by connection reference logical name or connector, never by instance id), Dataverse tables, and connected data sources added or removed; media hashes; `AppVersion`, display name. A removed Dataverse column is matched in formulas of apps that use its table by schema or logical name (case-insensitive) and by display name, quoted or as a bare identifier. Not compared: app settings beyond layout and name, themes, Test Studio recordings (listed as test objects, low) | `Entropy/*`, `AppCheckerResult.sarif`, `checksum.json`, connection instance ids, database instance URLs and environment ids, option-set and view data source entries (listed, not flagged), timestamps |
| Custom control (PCF) | `CustomControls/CustomControl` with files under `Controls/<name>/`; default configurations under `customcontroldefaultconfigs` | `Name` | Version, manifest, properties, bundle and resource file hashes (a rebuilt bundle with the same version still counts as changed) | None |
| Web resource | `WebResources/WebResource` with the file at `FileName` (strip the leading slash) | `Name` | File content hash, type, dependencies | None |

## Security

| Component | Location | Identifier | Meaningful change | Ignore |
| --- | --- | --- | --- | --- |
| Security role | `Roles/Role` | `name` attribute (and `id`) | `RolePrivilege` entries: privilege name and `level` (None, Basic, Local, Deep, Global); added, removed, raised, lowered | None |
| Field security profile | `FieldSecurityProfiles/FieldSecurityProfile` | `name` | Column permissions (create, read, update), membership is environment data and not in the package | None |

## Logic and automation

| Component | Location | Identifier | Meaningful change | Ignore |
| --- | --- | --- | --- | --- |
| Process record | `Workflows/Workflow` | `WorkflowId` attribute, `Name` attribute; the remaining properties are child elements | `Category` (0 classic workflow, 1 dialog, 2 business rule, 3 action, 4 business process flow, 5 cloud flow, 6 desktop flow, 7 AI flow), `StateCode` and `StatusCode` (0/1 draft, 1/2 activated), `PrimaryEntity`, `Scope`, `Mode`, trigger settings, `JsonFileName` or `XamlFileName` | `IntroducedVersion` |
| Cloud flow | `Workflows/<name>-<guid>.json` | Linked from the process record | `properties.definition.triggers` (type, kind, inputs), `properties.definition.actions` recursively including `actions`, `else.actions`, `cases.*.actions`, `default.actions`; `runAfter` predecessors and outcome conditions (Succeeded, Failed, Skipped, TimedOut); switch `case` values; `properties.definition.parameters` (declarations) and `properties.parameters` (runtime bindings read by `@parameters()`); `properties.connectionReferences` (api name, logical name, `runtimeSource` embedded or invoker); parameters | `metadata.operationMetadataId` |
| Business rule, classic workflow, action, business process flow | `Workflows/<name>.xaml` or JSON when exported as such | Linked from the process record | Definition content (compare text where possible), activation state, scope | None |
| Desktop flow | Process record with category 6 plus definition file | Linked | Definition hash; details require Power Automate for desktop | None |
| Plug-in assembly | `SolutionPluginAssemblies/PluginAssembly` (older exports: `PluginAssemblies/PluginAssembly`) with the DLL at `PluginAssemblies/<name>-<guid>/<name>.dll` | Assembly name from `FullName`; when either package carries several versions of one assembly, name plus major.minor, with a lone entry paired to the closest version on the other side | Version in `FullName`, isolation mode, plug-in types (`PluginType` entries), DLL hash; the code itself is not inspected | None |
| Plug-in package | `pluginpackages/pluginpackage` with the NuGet package under `pluginpackages/<name>-<guid>/` | `name` or `uniquename` | Version, package file hash; dependent assemblies inside the package are not inspected | None |
| Plug-in step | `SdkMessageProcessingSteps/SdkMessageProcessingStep` | `SdkMessageProcessingStepId` attribute; `Name` is a label and is not unique (the registration tool's default name repeats across stages) | `SdkMessage`, `PrimaryEntity`, `Stage` (10 pre-validation, 20 pre-operation, 40 post-operation), `Mode` (0 synchronous, 1 asynchronous), `Rank`, `FilteringAttributes`, images, `StateCode`, configuration | None |
| Custom API | `customapis/customapi`, `customapirequestparameters`, `customapiresponseproperties` | `uniquename`; request parameters and response properties are identified by owning API (`customapiid`), kind, and `uniquename`, because names repeat across APIs and across the two kinds | Binding, bound table, parameters and properties, plug-in type, privileges, enabled for workflow | Descriptions |
| Service endpoint and webhook | `ServiceEndpoints/ServiceEndpoint` | `name` | URL, authentication, contract | Descriptions |
| AI Builder model and prompt | `msdyn_aimodels`, `msdyn_aiconfigurations`, `msdyn_aitemplates` (generic collections) | Record ID or name | Configuration JSON, published state | Timestamps |

## Configuration and integration

| Component | Location | Identifier | Meaningful change | Ignore |
| --- | --- | --- | --- | --- |
| Connection reference | `connectionreferences/connectionreference` | `connectionreferencelogicalname` | Connector ID, display name; a new reference needs a connection at import | None |
| Environment variable | `environmentvariabledefinitions/environmentvariabledefinition`; full exports add a folder per variable holding `environmentvariabledefinition.xml` and, when a value is packaged, `environmentvariablevalues.json` | `schemaname` | Type, default value, packaged current value (inline `environmentvariablevalues` or the folder JSON, merged into one comparison), secret store settings | None |
| Custom connector | `Connectors/Connector` (or lowercase `connectors`) plus files under `Connectors/<name>/` | Name | Connector record properties and file hashes (OpenAPI definition, icon); the definition itself is not parsed | Timestamps |
| Setting definition and app setting | `settingdefinitions`, `appsettings` (generic collections) | Unique name | Default and override values, scope | None |
| Email, mail merge, article, and contract templates | `Templates/EmailTemplates/EmailTemplate`, `Templates/MailMergeTemplates/MailMergeTemplate`, `Templates/KBArticleTemplates/KBArticleTemplate`, `Templates/ContractTemplates/ContractTemplate` | `name` | Subject, body, table | None |
| Report | `Reports/Report` with the RDL file at `FileName` | `name` | RDL hash, related tables, visibility; the RDL is not parsed | None |
| Duplicate detection rule, mobile offline profile, workqueue, Dataverse search configuration | Their own collections | Name or ID | Definition content | None |
| Translation | `Languages`, label elements with `languagecode` | Language code | Labels added or changed per language | Ordering |

## Copilot Studio and Power Pages

| Component | Location | Identifier | Meaningful change | Ignore |
| --- | --- | --- | --- | --- |
| Copilot Studio agent | `bots/bot` with files under `bots/` | `schemaname` | Name, language, authentication mode, publishing settings, configuration | Timestamps |
| Agent component (topic, knowledge source, tool, trigger, entity) | `botcomponents/botcomponent` | `schemaname` with `componenttype` | `data` (topic YAML or component definition), parent agent, state | Timestamps |
| Power Pages site and components | `powerpagesites`, `powerpagecomponents`, `powerpagesitelanguages` and related collections | ID or name | Component type, content, publishing state | Timestamps |

## Unpacked source layout

Source unpacked with `pac solution unpack` splits the same content into folders: `Other/Solution.xml`, `Other/Customizations.xml` (without the split-out parts), `Entities/<table>/Entity.xml` with `FormXml/`, `SavedQueries/`, `Visualizations/` subfolders, `Workflows/`, `Roles/`, `OptionSets/`, `WebResources/`, `PluginAssemblies/`, `CanvasApps/`, `environmentvariabledefinitions/`, `connectionreferences/`. The identifiers above still apply; compare matching files pairwise and treat a file present on only one side as an added or removed component.

## Component type codes

`RootComponents` and `MissingDependencies` entries in solution.xml carry a numeric `type`. Common values:

| Code | Component | Code | Component | Code | Component |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | Table | 29 | Process | 80 | Model-driven app |
| 2 | Column | 31 | Report | 95 | Service endpoint |
| 3 | Relationship | 36 | Email template | 91 | Plug-in assembly |
| 9 | Choice | 39 | Mail merge template | 92 | Plug-in step |
| 10 | Table relationship | 44 | Duplicate rule | 300 | Canvas app |
| 14 | Alternate key | 59 | Chart | 400 | AI project type |
| 20 | Security role | 60 | Form | 401 | AI project |
| 21 | Role privilege | 61 | Web resource | 402 | AI configuration |
| 24 | Form (classic) | 62 | Sitemap | 371 | Connector |
| 26 | View | 66 | Custom control | 372 | Connector |
| 70 | Field security profile | 71 | Field permission | 380 | Environment variable definition |
| 90 | Plug-in type | 93 | Plug-in step image | 381 | Environment variable value |

Codes 371 and 372 are both documented by Microsoft as Connector. Codes of 10000 and above are table-based components (connection references, environment variable records in some exports, Copilot Studio agent components, Power Pages records, and any custom table) and are environment specific; identify them by the schema name in the entry rather than the code.

## Noise that is safe to ignore by default

`IntroducedVersion`, `modifiedon`, `createdon`, `versionnumber`, `overwritetime`, `solutionid`, `supportingsolutionid`, `ismanaged`, element ordering inside unordered collections (order is compared only where it carries meaning: form tabs, sections, columns, rows, and cells; view columns and sort; sitemap areas, groups, and subareas; choice options; process stages and steps), whitespace and GUID brace or case differences, and `metadata.operationMetadataId` in flow JSON. Everything else is a candidate change until shown otherwise.
