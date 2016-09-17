function kwlog(...args) {
  if (window.KWDEBUG === true ||
      window.KW.user.name === 'duncantest' || // local dev
      window.KW.user.name === 'Subversity' ||
      window.KW.user.name === 'Tadgh') {
    console.log(...args);
  }
}

export default kwlog;
