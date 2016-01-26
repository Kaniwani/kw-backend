const pluralize = function(text, num) {
  num = +num;
  if (Number.isNaN(num)) console.warn('pluralize received non-number');
  return `${num} ${text + (num > 1 || num == 0 ? "s" : "")}`;
}

export default pluralize;
