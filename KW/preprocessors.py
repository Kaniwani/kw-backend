from kw_webapp.constants import KANIWANI_SRS_LEVELS
from kw_webapp.tasks import get_users_future_reviews, get_users_current_reviews, get_users_reviews


def review_count_preprocessor(request):
    if hasattr(request, 'user'):
        if hasattr(request.user, 'profile'):
            context_dict = {}
            review_count = get_users_current_reviews(request.user).count()
            if review_count > 0:
                context_dict['review_count'] = review_count
            else:
                reviews = get_users_future_reviews(request.user)
                if reviews:
                    next_review_timestamp = reviews[0].next_review_date
                    context_dict['next_review_date'] = next_review_timestamp
            return context_dict

    return {'review_count': 0}


def srs_count_preprocessor(request):
    if hasattr(request, 'user'):
        if hasattr(request.user, 'profile'):
            context_dict = {}
            all_reviews = get_users_reviews(request.user)
            if all_reviews:
                context_dict['srs_apprentice_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['apprentice']).count()
                context_dict['srs_guru_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['guru']).count()
                context_dict['srs_master_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['master']).count()
                context_dict['srs_enlightened_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['enlightened']).count()
                context_dict['srs_burned_count'] = all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS['burned']).count()
            return context_dict
