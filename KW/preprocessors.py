from django.db.models import Min
from kw_webapp.models import UserSpecific

def review_count_preprocessor(request):
    if hasattr(request, 'user'):
        if hasattr(request.user, 'profile'):
            review_count = UserSpecific.objects.filter(user=request.user, needs_review=True).count()
            if review_count > 0:
                return {'review_count': review_count}
            else:
                reviews = UserSpecific.objects.filter(user=request.user).exclude(next_review_date=None).annotate(Min('next_review_date')).order_by('next_review_date')
                if reviews:
                    next_review_timestamp = reviews[0].next_review_date
                    return {'next_review_date': next_review_timestamp}
    return {'review_count': 0}
