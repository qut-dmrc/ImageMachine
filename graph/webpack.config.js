const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');

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
    devServer: {
        contentBase: path.join(__dirname, "dist"),
        port: 8080
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js']
    },
    output: {
        filename: 'main.js',
        publicPath: "/js",
        path: path.resolve(__dirname, 'dist')
    },
    devtool: "source-map"
};
