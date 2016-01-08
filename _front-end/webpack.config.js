var path = require('path');
var webpack = require('webpack');

module.exports = function(fabricatorConfig) {

	"use strict";

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
			loaders: [
				{
					test: /\.js$/,
					exclude: /(node_modules|prism\.js)/,
					loaders: ['babel-loader']
				}
			]
		},
		// pull in the simplestorage.js file that is loaded in reviews html template
		externals: {
	    simpleStorage: 'simpleStorage'
	  },
	  // expose it to webpack modules without having to import/require
	  plugins: [
	    new webpack.ProvidePlugin({
	      simpleStorage: 'simpleStorage',
	      $: 'jquery'
	    })
	  ],
		cache: {}
	};

	if (fabricatorConfig.prod != null) {
		config.plugins.push(
			new webpack.optimize.UglifyJsPlugin()
		);

		config.entry = {
			'scripts/global': fabricatorConfig.src.scripts.toolkit
		};
	}

	return config;

};
