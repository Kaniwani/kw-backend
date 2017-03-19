import time
import datetime

from kw_webapp import constants
from kw_webapp.constants import KANIWANI_SRS_LEVELS
from kw_webapp.tasks import get_users_future_reviews, get_users_current_reviews, get_users_reviews


def review_count_preprocessor(request):
    """
    preprocessor which returns user's review information like the following:
    1) Current review count.
    2) If no reviews, when is next review.
    3) How many reviews coming up in next hour.
    4) How many reviews coming up in next day.
    """
    context_dict = {}
    if hasattr(request, 'user'):
        if hasattr(request.user, 'profile'):
            review_count = get_users_current_reviews(request.user).count()
            context_dict['review_count'] = review_count
            if review_count == 0:
                reviews = get_users_future_reviews(request.user)
                if reviews:
                    next_review_date = reviews[0].next_review_date
                    context_dict['next_review_date'] = next_review_date
                    context_dict['next_review_timestamp_local'] = next_review_date.timestamp() * 1000
                    context_dict['next_review_timestamp_utc'] = int(time.mktime(next_review_date.timetuple())) * 1000 #TODO potentially remove?
            one_hour = datetime.timedelta(hours=1)
            today = datetime.timedelta(hours=24)
            return context_dict
    return context_dict



