const config = {
  toastr: {
    "preventDuplicates": true,
    "positionClass": "toast-top-right",
    "timeOut": "5000",
    "extendedTimeOut": "3000",
  },
  timeago: {
    settings: {
      allowFuture: true,
      allowPast: false,
    },
    strings: {
      prefixFromNow: '~',
      suffixFromNow: "",
      minute: 'a minute',
      hour: 'an hour',
      hours: '%d hours',
      month: 'a month',
      year: 'a year',
    },
  }
}

export default config;
