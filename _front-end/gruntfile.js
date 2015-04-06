module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    copy: {
      //Copy Dev
      html: {
        expand: true,
        src: '**/*.html',
        dest: 'build', 
        cwd: 'source'
      },

      fonts: {
        expand: true,
        src: '**/*',
        dest: 'build/static/fonts',
        cwd: 'source/fonts'
      },

      imgs: {
        expand: true,
        src: '**/*',
        dest: 'build/static/img',
        cwd: 'source/img'
      },

      //Copy dist
      fontsDist: {
        expand: true,
        src: '**/*',
        dest: 'dist/fonts',
        cwd: 'source/fonts'
      },

      imgsDist: {
        expand: true,
        src: '**/*',
        dest: 'dist/img',
        cwd: 'source/img'
      },

      dist: {
        expand: true,
        src: '**/*',
        dest: '../kw_webapp/static',
        cwd: 'dist'
      }
    },

    //Check JavaScript quality
    jshint: {
      all: ['source/js/components/**/*', 'source/js/helpers/**/*.js', 'source/js/scripts.js'],
      options: {
        jshintrc: '.jshintrc',
      }
    },

    //Code Kit / PrePros script append/prepend processing
    codekit: {
      dev: {
        files : {
          'build/static/js/scripts.js' : 'source/js/scripts.js',
          'build/static/js/head-scripts.js' : 'source/js/head-scripts.js'
        }
      },

      dist: {
        files : {
          'dist/js/scripts.js' : 'source/js/scripts.js',
          'dist/js/head-scripts.js' : 'source/js/head-scripts.js',
        }
      }
    },

    //Minify the JavaScript into the build folder
    uglify: {
      scripts: {
        files: {
          '../kw_webapp/static/js/scripts.min.js' : ['dist/js/scripts.js'],
          '../kw_webapp/static/js/head-scripts.min.js' : ['dist/js/head-scripts.js']
        }
      }
    },

    //Lint the SCSS as per coding standards
    scsslint: {
      options: {
        config: '.scss-lint.yml',
        reporterOutput: 'scss-lint-report.xml',
        colorizeOutput: true
      },
        
      allFiles: [
        'source/scss/**/*.scss', '!source/scss/vendor/**/*.scss'
      ]
    },

    //Compass task to build SASS/SCSS files into CSS
    compass: {
      dist: {
        options: {
          bundleExec: true,
          require: ['breakpoint'],
          sassDir: 'source/scss',
          cssDir: 'dist/css',
          environment: 'production'
        }
      },

      dev: {
        options: {
          bundleExec: true,
          require: ['breakpoint'],
          sassDir: 'source/scss',
          cssDir: 'build/static/css'
        }
      }
    },

    //Connect server for running the pattern library
    connect: {
      server: {
        options: {
          hostname: '0.0.0.0',
          port: 1337,
          base: 'build',
          livereload: true
        }
      }
    },

    //Watch task with livereload
    watch: {
      html: {
        files: ['source/**/*.html'],
        tasks: ['copy:html']
      },
      
      scripts: {
        files: ['source/js/**/*.js'],
        tasks: ['jshint','codekit']
      },

      styles: {
        files: 'source/scss/**/*.scss',
        tasks: ['scsslint', 'compass']
      },

      images: {
        files: ['source/img/**/*'],
        tasks: ['copy:imgs']
      },

      fonts: {
        files: ['source/fonts/**/*'],
        tasks: ['copy:fonts']
      },

      livereload: {
        files: ['build/**/*'],
        options: {
          livereload: true
        }
      }
    }
    

  });

  // Load JavaScript quality check task.
  grunt.loadNpmTasks('grunt-contrib-jshint');

  // Load uglify task.
  grunt.loadNpmTasks('grunt-contrib-uglify');

  //Load compass task
  grunt.loadNpmTasks('grunt-contrib-compass');

  //Load copy task
  grunt.loadNpmTasks('grunt-contrib-copy');

  //JavaScript append/prepend task
  grunt.loadNpmTasks('grunt-codekit');

  //Serve up the pattern library
  grunt.loadNpmTasks('grunt-contrib-connect');
  
  //SCSS lint
  grunt.loadNpmTasks('grunt-scss-lint');

  //Watch task
  grunt.loadNpmTasks('grunt-contrib-watch');

  //Load local grunt tasks
  // -- common-tasks.js - Common tasks across, pattern library, kitchen sink and build projects
  //grunt.loadTasks('./grunt-tasks');

  // Default task(s).
  grunt.registerTask('default', [
    'copy:html',
    'copy:fonts',
    'copy:imgs',
    'jshint',
    'codekit:dev',
    'scsslint',
    'compass:dev',
    'connect:server',
    'watch'
  ]);

  // Do everything that default does, without the wact or server.
  grunt.registerTask('build', [
    'copy:html',
    'copy:fonts',
    'copy:imgs',
    'jshint',
    'codekit:dev',
    'scsslint',
    'compass:dev'
  ]);

  // Production task
  grunt.registerTask('dist', [
    'jshint',
    'codekit:dist',
    'scsslint',
    'compass:dist',
    'copy:fontsDist',
    'copy:imgsDist',
    'copy:dist',
    'uglify'
  ]);
};
