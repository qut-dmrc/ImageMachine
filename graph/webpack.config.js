const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');
// const pythonProcess = spawn('python',[".././ml/imagemachine.py"]);
// const { execFile } = require('child_process');
// const child = execFile('python', ['.././ml/imagemachine.py'], (error, stdout, stderr) => {
//     if (error) {
//       throw error;
//     }
//     console.log(stdout);
//   });


module.exports = {
    // entry: './src/index.ts',
    mode: "development",
    module: {
        rules: [
            {
                test: /\.ts(x?)$/,
                use: 'ts-loader',
                exclude: /node_modules/
            },
            {
                enforce: "pre",
                test: /\.js$/,
                loader: "source-map-loader"
            }
        ]
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js']
    },
    output: {
        filename: 'main.js',
        publicPath: "/js",
        path: path.resolve(__dirname, 'dist')
    },
    plugins: [
        new CopyPlugin([
            {from: 'static/clusters.json', to: 'clusters.json'}
        ]),
    ],
    devtool: "source-map"
};
