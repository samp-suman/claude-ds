# Domain Reference: Social Media

## Key Performance Indicators (KPIs)
- Engagement rate (interactions / reach)
- Virality coefficient (K-factor)
- Sentiment score (positive/negative/neutral ratio)
- Reach and impressions
- Follower growth rate
- Content amplification ratio (shares / posts)
- Response time
- Community health score

## Critical Social Media Features

| Feature | Typical Range | Significance |
|---------|-------------|--------------|
| Engagement rate | 1–5% | > 5% = viral potential, < 1% = low engagement |
| Like-to-comment ratio | 10:1–50:1 | Low ratio = deeper engagement |
| Share-to-like ratio | 1:10–1:50 | High = amplification, content resonance |
| Follower growth rate | 1–5%/month | > 10% = suspicious (may be bots) |
| Post frequency | 1–5/day | Platform-dependent optimal ranges |
| Response rate | 70–90% | Brand health indicator |
| Sentiment polarity | -1 to +1 | Compound sentiment score |

## Domain-Specific Feature Engineering
- **Engagement metrics**: Likes, comments, shares, saves — weight differently by platform
- **Content features**: Text length, hashtag count, media type (image/video/text), emoji usage
- **Temporal features**: Hour of day, day of week, time since last post
- **Network features**: Follower count, following ratio, mutual connections
- **Sentiment scores**: Compound, positive, negative, neutral from text analysis
- **Virality indicators**: Early engagement velocity (likes in first hour), share-to-view ratio
- **User behavior patterns**: Posting frequency, response time, content consistency
- **Platform-specific**: Retweet vs quote-tweet, story views vs feed views, reel completion rate
- **Bot detection features**: Account age, posting pattern regularity, follower/following ratio
- **Hashtag features**: Hashtag popularity, trending status, niche vs broad

## Common Pitfalls
1. **Vanity metrics**: Follower count without engagement rate is misleading
2. **Bot contamination**: 5-15% of social accounts are bots — skew engagement metrics
3. **Platform algorithm changes**: Engagement baselines shift when algorithms update
4. **Sentiment analysis limitations**: Sarcasm, irony, and context-dependent meaning
5. **Temporal confounding**: Viral events create spikes that aren't repeatable patterns
6. **Echo chamber effects**: Engagement in echo chambers doesn't indicate broad appeal
7. **Cross-platform inconsistency**: Metrics don't translate across platforms (Instagram engagement ≠ Twitter engagement)

## Preferred Metrics
- **Content classification**: F1, precision-recall (multi-class: micro/macro)
- **Sentiment analysis**: F1 (3-class), correlation with human ratings
- **Engagement prediction**: RMSE, MAE, R² (treating as regression)
- **Bot detection**: Precision (minimize false positives on real users), F1
- **Virality prediction**: AUC-ROC, top-decile lift

## Analysis Types
- **Sentiment analysis**: VADER, TextBlob, or fine-tuned transformers
- **Topic modeling**: LDA, NMF, BERTopic for content categorization
- **Network analysis**: Influence scoring, community detection, information cascade
- **Time series**: Posting patterns, engagement trends, follower growth
- **Anomaly detection**: Bot detection, fake engagement, unusual behavior patterns

## Text-Specific Considerations
- **Preprocessing**: Handle @mentions, #hashtags, URLs, emojis as features not noise
- **Short text**: Social posts are short — TF-IDF may underperform vs embeddings
- **Multilingual**: Social data often contains multiple languages in one dataset
- **Emoji as features**: Emoji usage patterns carry sentiment and engagement signals
- **URL expansion**: Shortened URLs may indicate link type (news, product, spam)

## Red Flags
- Engagement model doesn't account for follower count (absolute engagement ≠ engagement rate)
- Sentiment model tested on formal text, applied to social text (domain mismatch)
- Bot detection model uses only account-level features without behavioral patterns
- Viral prediction ignores network structure and early engagement velocity
- Text features processed without handling platform-specific tokens (@, #, RT)
