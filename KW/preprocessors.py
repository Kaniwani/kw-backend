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
            context_dict['reviews_within_hour_count'] = get_users_future_reviews(request.user, time_limit=one_hour).count()
            context_dict['reviews_within_day_count'] = get_users_future_reviews(request.user, time_limit=today).count()
            return context_dict
    return context_dict


def srs_level_count_preprocessor(request):
    """
    Preprocessor to provide the user's specific SRS level information, indicating how many vocab exist at each SRS level.
    """
    context_dict = {}
    if hasattr(request, 'user'):
        if hasattr(request.user, 'profile'):
            all_reviews = get_users_reviews(request.user)
            if all_reviews:
                context_dict['srs_apprentice_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['apprentice']).count()
                context_dict['srs_guru_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['guru']).count()
                context_dict['srs_master_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['master']).count()
                context_dict['srs_enlightened_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['enlightened']).count()
                context_dict['srs_burned_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['burned']).count()
                context_dict['srs_level_names'] = constants.KANIWANI_SRS_LEVELS.keys()
    return context_dict


