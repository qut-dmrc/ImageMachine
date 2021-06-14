const path = require("path");
const CopyPlugin = require("copy-webpack-plugin");
const webpack = require("webpack");

module.exports = (CLUSTER_NAME) => {
    return {
        entry: "./src/index.ts",
        mode: "development",
        module: {
            rules: [
                {
                    test: /\.ts(x?)$/,
                    use: "ts-loader",
                    exclude: /node_modules/,
                },
                {
                    enforce: "pre",
                    test: /\.js$/,
                    loader: "source-map-loader",
                },
            ],
        },
        devServer: {
            contentBase: path.join(__dirname, "dist"),
            host: "0.0.0.0",
            port: 8080,
            disableHostCheck: true,
        },
        resolve: {
            extensions: [".tsx", ".ts", ".js"],
        },
        output: {
            filename: "main.js",
            publicPath: "/js",
            path: path.resolve(__dirname, "dist"),
        },
        plugins: [
            new webpack.DefinePlugin({
                "process.env.CLUSTER_NAME": JSON.stringify(CLUSTER_NAME),
            }),
        ],
        devtool: "inline-source-map",
    };
};
