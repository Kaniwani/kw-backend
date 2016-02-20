// map python True/False passed from view as strings to JS true/false booleans
const strToBoolean = function(o) {
  if (o == null) {
    console.warn('Invalid input provided to strToBoolean:', o);
    return;
  }
  for (let k of Object.keys(o)) {
    let v = o[k];
    o[k] = (v === 'True' ? true : false);
  }
  return o;
};

export default strToBoolean;
