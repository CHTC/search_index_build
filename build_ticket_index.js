// Generates the serialized idx object that runs the search bar
// Based on the Lunr build process https://lunrjs.com/guides/index_prebuilding.html
//
// Assumes documents are at ./documents.json

const fs = require('fs')
const lunr = require('lunr')

// Read in the JSON that contains the index arguments and set them
let args = {}
try {
    args = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))
} catch (err) {
    console.error(err)
}
let ref = args.ref
let fields = args.fields
let index_output = args.index_output

// Read in the documents that compose the content to be indexed
let documents = []
try {
    documents = JSON.parse(fs.readFileSync("./documents.json", 'utf8'))
} catch (err) {
    console.error(err)
}

// Build the lunr idx object https://lunrjs.com/guides/getting_started.html#creating-an-index
let idx = lunr(function () {
    this.ref(ref)
    fields.forEach(function(field){
        if("boost" in field){
            this.field(field.id, field.boost)
        } else {
            this.field(field.id)
        }
    }, this)

    documents.forEach(function (doc) {
        this.add(doc)
    }, this)
})

// Write the file out
fs.writeFile(index_output, JSON.stringify(idx), err => {
    if (err) {
        console.error(err)
        return
    }
    //file written successfully
})
