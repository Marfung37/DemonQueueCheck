const {decoder, encoder} = require('tetris-fumen');

let input = process.argv.slice(2);
let fumen = input[0];
let comment = input[1];

let page = decoder.decode(fumen)[0];
page.comment = comment;

let fumenWComment = encoder.encode([page]);
console.log(fumenWComment)