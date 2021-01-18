d3.json("data.json").then(function(data){
    let imagePaths = []
    let imageNames = []
    //start from node 195
    while(data['name'] != 195){
        data = data['children'][1]
    }
    getImagePath(imagePaths, imageNames, data)
    for(var path in imagePaths){
        console.log(imageNames[path] + imagePaths[path])
    }
})


//get imagepath from a particular point
function getImagePath(imagePaths, imageNames, data) {
    if(data.metadata != null && Object.keys(data.metadata).length !== 0){
        imagePaths.push(data['metadata']['_mediaPath'][0])
        imageNames.push(data['name'])
    }
    if(data.children != null && data.children.length !== 0){
        for(let i =0; i<data.children.length; i++){
            getImagePath(imagePaths, imageNames, data.children[i])
        }
    }
}