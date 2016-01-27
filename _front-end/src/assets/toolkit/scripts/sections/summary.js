import refreshReviews from '../components/refreshReviews';

let init = function() {
	// are we on summary page?
	if (/summary/.test(window.location.pathname)) {
		refreshReviews({forceGet: true});
	}
}

const api = {
	init,
};

export default api;
