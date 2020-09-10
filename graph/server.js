
if(process.env.NODE_ENV !== 'production'){
    require('dotenv').config({path:'.env'})
}

const express = require('express')
const app = express()

app.set('view engine', 'ejs')
app.set('views', __dirname +'/views')
app.use(express.static('public'))

app.get('/',(req,res)=>{
    res.render('index.ejs')
})

app.listen(process.env.PORT || 3000)
