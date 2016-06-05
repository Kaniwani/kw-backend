// only log is debug turned on
const kwlog = function (...args) {
  if (window.KWDEBUG === true) {
    console.log(...args);
  }
};

export default kwlog;
