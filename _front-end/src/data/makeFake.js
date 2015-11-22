var f = require('faker');
var fs = require('fs');

// a collection for the json
var users = [];

// add 10 randomized user cards to collection
var i = 11;
while(i--) {
  users.push(f.helpers.userCard())
}

// add users as collection in json
var data = {
  users: users
};

// write json
fs.writeFile('fake.json', JSON.stringify(data), function (err) {
  if (err) throw err;
  console.log('It\'s saved!');
});
