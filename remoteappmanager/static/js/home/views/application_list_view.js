define([
    '../../components/vue/dist/vue',
], function (Vue) {
    'use strict';

    var ApplicationListView = Vue.extend({
        template:
            '<section class="sidebar">' +
              '<!-- Search form -->' +
              '<form action="#" class="sidebar-form">' +
              '  <input type="text" name="q" class="form-control" placeholder="Search..." v-model="search_input">' +
              '</form>' +

              '<!-- Sidebar Menu -->' +
              '<ul class="sidebar-menu">' +
              '  <li class="header">APPLICATIONS</li>' +
              '</ul>' +

              '<ul class="sidebar-menu">' +
              '  <li v-show="!model.loading && model.app_list.length === 0" id="no-app-msg">' +
              '    <a href="#">No applications found</a>' +
              '  </li>' +

              '  <!-- Loading spinner -->' +
              '  <li v-show="model.loading" id="loading-spinner">' +
              '    <a href="#">' +
              '      <i class="fa fa-spinner fa-spin"></i>' +
              '      <span>Loading</span>' +
              '    </a>' +
              '  </li>' +
              '</ul>' +

              '  <!-- Application list -->' +
              '<transition-group name="list" tag="ul" id="applistentries" class="sidebar-menu">' +
              '  <li v-for="app in visible_list" v-bind:key="app"' +
              '      :class="{ active: index_of(app) === model.selected_index }"' +
              '      @click="model.selected_index = index_of(app); $emit(\'entry_clicked\');">' +

              '    <span :class="app.status.toLowerCase() + \'-badge\'"></span>' +

              '    <a href="#" class="truncate">' +
              '      <img class="app-icon"' +
              '           :src="app.app_data.image.icon_128 | icon_src">' +

              '      <button class="stop-button"' +
              '              v-if="app.is_running()"' +
              '              @click="model.stop_application(index_of(app))"' +
              '              :disabled="app.is_stopping()">' +
              '        <i class="fa fa-times"></i>' +
              '      </button>' +
              '      <span>{{ app.app_data.image | app_name }}</span>' +
              '    </a>' +
              '  </li>' +
              '</transition-group>' +
              '<!-- /.sidebar-menu -->' +
            '</section>' +
            '<!-- /.sidebar -->',

        data: function() {
            return { 'search_input': '' };
        },

        computed: {
            visible_list: function() {
                return this.model.app_list.filter(function(app) {
                    var app_name = this.$options.filters.app_name(app.app_data.image).toLowerCase();
                    return app_name.indexOf(this.search_input.toLowerCase()) !== -1;
                }.bind(this));
            }
        },

        methods: {
            index_of: function(app) {
                return this.model.app_list.indexOf(app);
            }
        }
    });

    return {
        ApplicationListView : ApplicationListView
    };
});
