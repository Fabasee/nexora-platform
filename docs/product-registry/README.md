# Nexora Master Product Registry

The canonical seed is `master-product-registry.json`. It records the portfolio independently from the runtime `Product` table.

## Why there are two registries

- **Portfolio registry** (`ProductPortfolioEntry`): all approved directions, candidate products, modules and shared platform services, including work that is still planned or under research.
- **Runtime product registry** (`Product`): only products that are explicitly configured for account membership, subscription and activation.

A portfolio entry does not become visible in the consumer product catalog simply because it exists in this manifest. The manifest importer never creates or activates a runtime `Product`, never creates memberships, and never grants entitlements.

## Classification

- `entry_type`: application, module, or platform service.
- `parent_key`: modules must belong to a parent application.
- `decision_status=confirmed`: the product direction or module was explicitly established in prior planning.
- `decision_status=candidate`: a proposed product or grouping that still needs validation.
- `lifecycle_status`: delivery maturity; it is not a public availability switch.
- `priority`: core, viral, strategic, supporting, or future.
- `delivery_model`: standalone app, module, or shared service.

The registry deliberately preserves concepts without turning each concept into a separate app. In particular, Pulse, Drama, Creator AI, Circle, FanZone and GameHub are currently candidate modules, not approved standalone applications. Their parent mappings are provisional and must be validated before implementation.

## Current portfolio outline

### Confirmed directions and existing projects

- Nexora Core — shared platform foundation.
- Day-Date — dating and relationship product.
- Nexora Muslim — Muslim-oriented product.
- Dignity — education, with e-learning, attendance, SIAKAD, research and library modules.
- Nexverse — digital reading, video and music.
- Nexora Finance — finance product, with Accounting & BI as one domain among several.
- Nexora Business Suite — creator/business administration, regional publisher operations and campus registration.
- Nexora Office — private owner/employee operations and monitoring console, not a public coworking product.
- Nexora Studio — creative and digital service operations.
- Nexora Intelligent Vision & IoT — personal hybrid vision/IoT research, prioritizing biomedical vital monitoring and automated alerts.
- Nexora BioMotion — retained as a research candidate under Intelligent Vision & IoT.

### Candidate parent products and platform services

Nexora Social, Nexora Beyond, Nexora Market, Nexora AI, Nexora Health and Nexora Life remain candidate or planned directions, not claims of completed applications. Nexora Cloud, Nexora Launch and Nexora Web are proposed shared platform services.

## Synchronize into Django

From `services/api`:

```bash
python manage.py migrate
python manage.py sync_product_registry --dry-run
python manage.py sync_product_registry
```

The command is idempotent and non-destructive: it creates or updates manifest entries and does not delete entries that are not in the manifest. Use `--manifest /path/to/file.json` to validate or import another manifest.

Review changes to the JSON manifest through pull requests. Do not use the manifest to publish products, enable subscriptions or grant access; those remain separate operational decisions.
