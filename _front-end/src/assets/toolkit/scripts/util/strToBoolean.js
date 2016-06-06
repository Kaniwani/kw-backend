import kwlog from './kwlog';

// map python True/False passed from view as strings to JS true/false booleans
function strToBoolean(obj) {
  if (obj == null) {
    kwlog('Invalid input provided to strToBoolean:', obj);
  } else {
    for (let key of Object.keys(obj)) {
      const val = obj[key];
      obj[key] = !!(val === 'True');
    }
  }

  return obj;
}

export default strToBoolean;
