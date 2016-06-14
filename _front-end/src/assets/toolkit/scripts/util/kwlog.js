function kwlog(...args) {
  if (window.KWDEBUG === true || window.KW.user.name === 'Subversity') {
    console.log(...args);
  }
}

export default kwlog;
