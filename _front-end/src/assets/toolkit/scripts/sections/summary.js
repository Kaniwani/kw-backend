import { refreshReviews } from '../components/refreshReviews';
import { adjustCardHeight } from '../sections/levelVocab';

let init = function() {
	// are we on summary page?
	if (/summary/.test(window.location.pathname)) {
		refreshReviews({forceGet: true});
    adjustCardHeight($('.vocab-list .vocab-card'));
	}
}

const api = {
	init,
};

export default api;
