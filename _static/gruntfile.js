module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    //Copy html
    copy: {
      html: {
        expand: true,
        src: '**/*.html',
        dest: 'build', 
        cwd: 'source'
      },

      fontassets: {
        expand: true,
        src: '**/*',
        dest: 'build/assets/fonts',
        cwd: 'source/fonts'
      },

      imgassets: {
        expand: true,
        src: '**/*',
        dest: 'build/assets/img',
        cwd: 'source/img'
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
      jsinclude : {
        files : {
          'build/assets/js/scripts.js' : 'source/js/scripts.js'
        }
      }
    },

    //Minify the JavaScript into the build folder
    uglify: {
      scripts: {
        files: {
          'build/assets/js/min/scripts.min.js' : ['build/assets/js/scripts.js']
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
          cssDir: 'dist/assets/css',
          environment: 'production'
        }
      },
      dev: {
        options: {
          bundleExec: true,
          require: ['breakpoint'],
          sassDir: 'source/scss',
          cssDir: 'build/assets/css'
        }
      }
    },

    //Connect server for running the pattern library
    connect: {
      server: {
        options: {
          hostname: '127.0.0.1',
          port: 8888,
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
        tasks: ['compass']
      },

      images: {
        files: ['source/img/**/*'],
        tasks: ['copy:imgassets']
      },

      fonts: {
        files: ['source/fonts/**/*'],
        tasks: ['copy:fontassets']
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
    'copy',
    'jshint',
    'codekit',
    'scsslint',
    'compass:dev',
    'connect:server',
    'watch'
  ]);

  // Production task
  grunt.registerTask('dist', [
    'copy',
    'jshint',
    'codekit',
    'uglify',
    'scsslint',
    'compass:dist'
  ]);
};