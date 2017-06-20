var path = require('path');
var webpack = require('webpack');

module.exports = function(fabricatorConfig) {
  var config = {
    entry: {
      'fabricator/scripts/f': fabricatorConfig.src.scripts.fabricator,
      'scripts/global': fabricatorConfig.src.scripts.toolkit
    },
    output: {
      path: path.resolve(__dirname, fabricatorConfig.dest, 'assets'),
      filename: '[name].js'
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /(node_modules|prism\.js)/,
          use: [{
            loader: 'babel-loader'
          }],
        }
      ]
    },
    plugins: [
      new webpack.ProvidePlugin({
        $: 'jquery',
        notie: 'notie',
        simpleStorage: 'simplestorage.js',
      })
    ],
    cache: {}
  };

  if (fabricatorConfig.prod != null) {
    config.plugins.push(
      new webpack.optimize.DedupePlugin(),
      new webpack.optimize.UglifyJsPlugin()
    );

    config.entry = {
      'scripts/global': fabricatorConfig.src.scripts.toolkit
    };
  }

  return config;

};
