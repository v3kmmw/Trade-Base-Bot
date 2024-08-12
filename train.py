from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize the VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Example texts
texts = [
    "I love this product, it's fantastic!",
    "This is a terrible product, very bad experience.",
    "The service was okay, not great but not terrible.",
    "Absolutely wonderful, would buy again!",
    "Horrible! The worst I've ever seen.",
]

# Analyze the sentiment of each text
for text in texts:
    scores = analyzer.polarity_scores(text)
    print(f"Text: {text}")
    print(f"Sentiment Scores: {scores}")
    print("\n")