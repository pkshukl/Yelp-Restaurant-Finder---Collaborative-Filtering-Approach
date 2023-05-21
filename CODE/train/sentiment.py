from textblob import TextBlob


def Score_Restaurant(business_id, restaurant_reviews):
    business_reviews = restaurant_reviews[restaurant_reviews['business_id'] == business_id]

    business_reviews.dropna(subset=['stars_y', 'text'], inplace=True)

    sentiment_scores = []
    for review in business_reviews['text']:
        blob = TextBlob(review)
        sentiment_scores.append(blob.sentiment.polarity)

    if sentiment_scores:
        sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
    else:
        sentiment_score = 0

    return sentiment_score


def Score_All_Restaurants(restaurant_reviews):
    restaurant_reviews.dropna(subset=['business_id'], inplace=True)

    sentiment_scores = {}
    for business_id in restaurant_reviews['business_id'].unique():
        business_reviews = restaurant_reviews[restaurant_reviews['business_id'] == business_id]
        business_reviews.dropna(subset=['stars_y', 'text'], inplace=True)
        polarity_scores = []
        subjectivity_scores = []
        for review in business_reviews['text']:
            blob = TextBlob(review)
            polarity_scores.append(blob.sentiment.polarity)
            subjectivity_scores.append(blob.sentiment.subjectivity)
        if polarity_scores:
            polarity_score = sum(polarity_scores) / len(polarity_scores)
        else:
            polarity_score = 0
        if subjectivity_scores:
            subjectivity_score = sum(subjectivity_scores) / len(subjectivity_scores)
        else:
            subjectivity_score = 0
        sentiment_scores[business_id] = {'polarity': polarity_score, 'subjectivity': subjectivity_score}

    return sentiment_scores
