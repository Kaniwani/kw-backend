window.KaniWani = window.KaniWani || {};


KaniWani.utility = {
  /**
   * Checks to see if the url is an internal hash
   * @param   {string}    url - url being evaluated
   * 
   */
  isHash: function (url) {
    var hasPathname = (url.indexOf(location.pathname) > 0) ? true : false,
      hasHash = (url.indexOf('#') > 0) ? true : false;
    return (hasPathname && hasHash) ? true : false;
  }
};


KaniWani.vars = {
  csrfToken: $('#csrf').val()
};


KaniWani.DOM = {
  $body: $('body')
};