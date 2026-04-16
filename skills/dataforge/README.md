# dataforge (Router)

The main entry point for all DataForge commands. Parses `/dataforge <command>` and delegates to the appropriate skill or workflow.

## Usage

```
/dataforge <command> [arguments]
```

You don't need to use this directly — it routes automatically when you type any `/dataforge` command.

## How routing works

| You type | Routes to |
|----------|-----------|
| `/dataforge run ...` | [dataforge-pipeline](../dataforge-pipeline/) |
| `/dataforge analyze ...` | [dataforge-analysis](../dataforge-analysis/) |
| `/dataforge eda ...` | [dataforge-eda](../dataforge-eda/) |
| `/dataforge preprocess ...` | [dataforge-preprocess](../dataforge-preprocess/) |
| `/dataforge train ...` | [dataforge-modeling](../dataforge-modeling/) |
| `/dataforge validate ...` | [dataforge-preprocess](../dataforge-preprocess/) |
| `/dataforge deploy ...` | [dataforge-deploy](../dataforge-deploy/) |
| `/dataforge report ...` | [dataforge-report](../dataforge-report/) |
| `/dataforge status ...` | [dataforge-experiment](../dataforge-experiment/) |
| `/dataforge resume ...` | [dataforge-pipeline](../dataforge-pipeline/) |
| `/dataforge monitor ...` | [dataforge-experiment](../dataforge-experiment/) |
