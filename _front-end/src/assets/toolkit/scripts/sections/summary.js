import { refreshReviews } from '../components/refreshReviews';

let init = function() {
	// are we on summary page?
	if (/summary/.test(window.location.pathname)) {
		// update from sessionstorage, we fake recentlyRefreshed at end of review'
		refreshReviews();
	}
}

const api = {
	init,
};

export default api;
