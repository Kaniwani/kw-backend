function kwlog(...args) {
  if (window.KWDEBUG === true) {
    console.log(...args);
  }
}

export default kwlog;
