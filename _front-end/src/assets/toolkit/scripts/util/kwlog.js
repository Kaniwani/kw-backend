export default function kwlog(...args) {
  if (window.KWDEBUG === true) {
    console.log(...args);
  }
}
