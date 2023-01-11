const {decoder, encoder} = require('tetris-fumen');

let fumens = process.argv.slice(2);

let pages = [];

for(let fumen of fumens){
    pages.push(...decoder.decode(fumen));
}

let combinedFumen = encoder.encode(pages);
console.log(combinedFumen)