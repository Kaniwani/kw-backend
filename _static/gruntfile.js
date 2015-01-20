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
        cwd: 'src'
      },

      fontassets: {
        expand: true,
        src: '**/*',
        dest: 'build/assets/fonts',
        cwd: 'src/fonts'
      },

      imgassets: {
        expand: true,
        src: '**/*',
        dest: 'build/assets/img',
        cwd: 'src/img'
      }
    },

    //Check JavaScript quality
    jshint: {
      all: ['src/js/components/**/*', 'src/js/helpers/**/*.js', 'src/js/scripts.js'],
      options: {
        jshintrc: '.jshintrc',
      }
    },

    //Code Kit / PrePros script append/prepend processing
    codekit: {
      jsinclude : {
        files : {
          'build/assets/js/scripts.js' : 'src/js/scripts.js'
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
        'src/scss/**/*.scss'
      ]
    },

    //Compass task to build SASS/SCSS files into CSS
    compass: {
      dist: {
        options: {
          require: ['breakpoint'],
          sassDir: 'src/scss',
          cssDir: 'dist/assets/css'
          environment: 'production'
        }
      },
      dev: {
        options: {
          require: ['breakpoint'],
          sassDir: 'src/scss',
          cssDir: 'build/assets/css'
        }
      }
    },

    //Connect server for running the pattern library
    connect: {
      server: {
        options: {
          hostname: '',
          port: 8888,
          base: 'build',
          livereload: true
        }
      }
    },

    //Watch task with livereload
    watch: {
      html: {
        files: ['src/**/*.html'],
        tasks: ['copy:html']
      },
      
      scripts: {
        files: ['src/js/**/*.js'],
        tasks: ['jshint','codekit']
      },

      styles: {
        files: 'src/scss/**/*.scss',
        tasks: ['compass']
      },

      images: {
        files: ['src/img/**/*'],
        tasks: ['copy:imgassets']
      },

      fonts: {
        files: ['src/fonts/**/*'],
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
    // 'uglify',
    'scsslint',
    'compass:dev',
    'connect:server',
    'watch'
  ]);

  // Production task
  grunt.registerTask('default', [
    'copy',
    'jshint',
    'codekit',
    'uglify',
    'scsslint',
    'compass:dist'
  ]);
};