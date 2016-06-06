'use strict';

// modules
var assemble = require('fabricator-assemble'),
    nano = require('gulp-cssnano'),
    del = require('del'),
    gulp = require('gulp'),
    gutil = require('gulp-util'),
    gulpif = require('gulp-if'),
    stripDebug = require('gulp-strip-debug'),
    imagemin = require('gulp-imagemin'),
    rename = require('gulp-rename'),
    runSequence = require('run-sequence'),
    sass = require('gulp-sass'),
    sassGlob = require('gulp-sass-glob'),
    sourcemaps = require('gulp-sourcemaps'),
    webpack = require('webpack'),
    changed = require('gulp-changed'),
    postcss = require('gulp-postcss'),
    responsiveType = require('postcss-responsive-type'),
    lost = require('lost'),
    autoprefixer = require('autoprefixer'),
    browserSync = require('browser-sync'),
    reload = browserSync.reload;


// configuration
var config = {
  dev: gutil.env.dev,
  prod: gutil.env.prod,
  src: {
    scripts: {
      fabricator: './src/assets/fabricator/scripts/fabricator.js',
      toolkit: './src/assets/toolkit/scripts/global.js'
    },
    styles: {
      fabricator: 'src/assets/fabricator/styles/fabricator.scss',
      toolkit: 'src/assets/toolkit/styles/main.scss'
    },
    images: 'src/assets/toolkit/images/**/*',
    fonts: 'src/assets/toolkit/fonts/**/*',
    views: 'src/views/*.html'
  },
  dest: 'dist'
};


// webpack
var webpackConfig = require('./webpack.config')(config);
var webpackCompiler = webpack(webpackConfig);


// clean
gulp.task('clean', function () {
  if (!config.prod) return del([config.dest]);
});


// styles
gulp.task('styles:fabricator', function () {
  gulp.src(config.src.styles.fabricator)
    .pipe(sourcemaps.init())
    .pipe(sass().on('error', sass.logError))
    .pipe(gulpif(config.prod, nano()))
    .pipe(rename('f.css'))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest(config.dest + '/assets/fabricator/styles'))
    .pipe(gulpif(!config.prod, reload({stream:true})));
});

gulp.task('styles:toolkit', function () {
  gulp.src(config.src.styles.toolkit)
    .pipe(gulpif(!config.prod, sourcemaps.init()))
    .pipe(sassGlob())
    .pipe(sass().on('error', sass.logError))
    .pipe(postcss([
      responsiveType(),
      lost(),
    ]))
    .pipe(gulpif(config.prod, nano({
      discardComments: {removeAll: true},
      autoprefixer: {browsers: ['last 2 versions', '> 1%']},
    })))
    .pipe(gulpif(!config.prod, sourcemaps.write()))
    .pipe(gulp.dest(config.dest + '/assets/styles'))
    .pipe(gulpif(!config.prod, reload({stream:true})));
});

gulp.task('styles', !config.prod ? ['styles:fabricator', 'styles:toolkit'] : ['styles:toolkit'] );


// scripts
gulp.task('scripts', function (done) {
  webpackCompiler.run(function (error, result) {
    if (error) {
      gutil.log(gutil.colors.red(error));
    }
    result = result.toJson();
    if (result.errors.length) {
      result.errors.forEach(function (error) {
        gutil.log(gutil.colors.red(error));
      });
    }
    done();
  });
});


// fonts
gulp.task('fonts', function () {
  return gulp.src(config.src.fonts)
    .pipe(changed(config.dest + '/assets/fonts'))
    .pipe(gulp.dest(config.dest + '/assets/fonts'));
});


// images
gulp.task('images', function () {
  return gulp.src(config.src.images)
    .pipe(changed(config.dest + '/assets/images'))
    .pipe(gulpif(config.prod, imagemin()))
    .pipe(gulp.dest(config.dest + '/assets/images'));
});

// assemble
gulp.task('assemble', function (done) {
  if (!config.prod) {
    assemble({
      logErrors: config.prod
    });
  }
  done();
});

// remove console.log statements
gulp.task('stripDebug', function () {
  return gulp.src(config.dest + '/assets/scripts/global.js')
        .pipe(stripDebug())
        .pipe(gulp.dest(config.dest + '/assets/scripts'));

});

// server
gulp.task('serve', function () {

  browserSync({
    server: {
      baseDir: config.dest
    },
    notify: false,
    logPrefix: 'FABRICATOR'
  });

  /**
   * Because webpackCompiler.watch() isn't being used
   * manually remove the changed file path from the cache
   */
  function webpackCache(e) {
    var keys = Object.keys(webpackConfig.cache);
    var key, matchedKey;
    for (var keyIndex = 0; keyIndex < keys.length; keyIndex++) {
      key = keys[keyIndex];
      if (key.indexOf(e.path) !== -1) {
        matchedKey = key;
        break;
      }
    }
    if (matchedKey) {
      delete webpackConfig.cache[matchedKey];
    }
  }

  gulp.task('assemble:watch', ['assemble'], reload);
  gulp.watch('src/**/*.{html,md,json,yml}', ['assemble:watch']);

  gulp.task('styles:fabricator:watch', ['styles:fabricator']);
  gulp.watch('src/assets/fabricator/styles/**/*.scss', ['styles:fabricator:watch']);

  gulp.task('styles:toolkit:watch', ['styles:toolkit']);
  gulp.watch('src/assets/toolkit/styles/**/*.scss', ['styles:toolkit:watch']);

  gulp.task('scripts:watch', ['scripts'], reload);
  gulp.watch('src/assets/{fabricator,toolkit}/scripts/**/*.js', ['scripts:watch'])
      .on('change', webpackCache);

  gulp.task('images:watch', ['images'], reload);
  gulp.watch(config.src.images, ['images:watch']);

});


// default build task
gulp.task('default', ['clean'], function () {

  // define build tasks
  var tasks = [
    'styles',
    'scripts',
    'images',
    'fonts',
    'assemble'
  ];

  // run build
  runSequence(tasks, function () {
    if (!config.prod) {
      gulp.start('serve');
    }

    if (config.prod) {
     // gulp.start('stripDebug');
    }
  });

});
