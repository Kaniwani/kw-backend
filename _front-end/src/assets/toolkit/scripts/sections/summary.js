function init() {
  if (/summary/.test(window.location.pathname)) {
    const pMatch = $('.correctPercent').text().match(/^\d*/);
    const percent = pMatch.length && pMatch[0];

    setTimeout(() => $('.percentage-bar .percentage').css('width', `${percent}%`), 200);
  }
}

const api = {
  init,
};

export default api;

