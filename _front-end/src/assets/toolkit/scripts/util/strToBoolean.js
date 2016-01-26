// map python True/False passed from view as strings to JS true/false booleans
const strToBoolean = function(o) {
  for (let k of Object.keys(o)) {
    let v = o[k];
    o[k] = (v === 'True' ? true : false);
  }
};

export default strToBoolean;
