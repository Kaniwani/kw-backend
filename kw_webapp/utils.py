from kw_webapp.models import UserSpecific, Vocabulary;
from kw_webapp.tasks import unlock_eligible_vocab_from_level
def wipe_all_reviews_for_user(user):
    reviews = UserSpecific.objects.filter(user=user)
    reviews.delete();
    reviews.save
    if len(reviews) > 0:
        raise ValueError
    else:
        print("deleted all reviews for " + user.username)



def unlock_level_for_user(level, user):
    unlock_eligible_vocab_from_level(user, level)

def flag_all_reviews_for_user(user, needed):
    reviews = UserSpecific.objects.filter(user=user)
    reviews.update(needs_review=needed)

