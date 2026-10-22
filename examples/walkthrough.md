# A coaching interaction

This is an independently written illustration of intended behavior, not an experimental result or a recorded success-rate claim. Study labels and values are fictional teaching material.

**Writer's request**

> Revise this results paragraph and explain the most important changes in Chinese. Keep the reported values and uncertainty.
>
> The revised scheduler is universally superior. In our test with 40 clients, median response time was 16 ms for the revised scheduler and 23 ms for the baseline. We measured no other load conditions. CPU use was 62% and 49%, respectively.

**Useful retrieval**

```bash
python scripts/lookup.py search "comparison conditions results tradeoff 比较条件" --limit 3 --json
python scripts/lookup.py get comparison.control-scope --json
```

**One suitable revision**

> With 40 clients, the revised scheduler had a median response time of 16 ms, compared with 23 ms for the baseline, while CPU use was 62% and 49%, respectively. Other load conditions were not measured.

**Explanation**

将比较限定在 40 个客户端这一已测条件，并用响应时间和 CPU 使用率展示实际取舍。原稿中的 universally superior 超出了证据范围，因此没有保留。修订保留了所有数值及其对应对象，也没有加入统计显著性或未测负载下的结论。

**Optional transfer exercise**

> In a different study, method P needs 3 minutes and 5 GB of memory; method Q needs 6 minutes and 2 GB. Both were tested on the same supplied dataset. Write two sentences that describe the tradeoff without ranking either method as best for every use case.

Let the writer respond before giving feedback. Check whether their comparison keeps the time and memory values attached to the correct methods and limits the comparison to the tested dataset. The goal is to assess their decision, not their ability to repeat a template.
