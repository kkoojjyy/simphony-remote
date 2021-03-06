var Vue = require("vue");
var toolkit = require("toolkit");

QUnit.module("ErrorDialog");
QUnit.test("rendering errors one by one", function (assert) {
  var done = assert.async();

  var errorDialog = new Vue(toolkit.ErrorDialog).$mount();

  Vue.nextTick(function() {
    // Error dialog not rendered (No error to show)
    assert.notEqual(errorDialog.$el.nodeType, Node.ELEMENT_NODE);

    errorDialog.errorList.push({title: "Oups"});
    errorDialog.errorList.push({code: 502});
    errorDialog.errorList.push({title: "Oups", message: "Something happened..."});

    Vue.nextTick(function() {
      assert.equal(
        errorDialog.$el.textContent,
        "Oups  unknown error Cancel Ok"
      );

      errorDialog.okCallback(); // Simulate click ok
      Vue.nextTick(function() {
        assert.equal(
          errorDialog.$el.textContent,
          "Error Code: 502 unknown error Cancel Ok"
        );

        errorDialog.okCallback(); // Simulate click ok
        Vue.nextTick(function() {
          assert.equal(
            errorDialog.$el.textContent,
            "Oups  Something happened... Cancel Ok"
          );

          errorDialog.okCallback(); // Simulate click ok
          Vue.nextTick(function() {
            // Error dialog not rendered (No error to show)
            assert.notEqual(errorDialog.$el.nodeType, Node.ELEMENT_NODE);

            done();
          });
        });
      });
    });
  });
});

QUnit.test("cancel showing errors", function (assert) {
  var done = assert.async();

  var errorDialog = new Vue(toolkit.ErrorDialog).$mount();

  Vue.nextTick(function() {
    errorDialog.errorList.push({title: "Oups"});
    errorDialog.errorList.push({code: 502});
    errorDialog.errorList.push({title: "Oups", message: "Something happened..."});

    Vue.nextTick(function() {
      assert.equal(
        errorDialog.$el.textContent,
        "Oups  unknown error Cancel Ok"
      );

      errorDialog.closeCallback(); // Simulate click close
      Vue.nextTick(function() {
        // Error dialog not rendered (Error list empty)
        assert.notEqual(errorDialog.$el.nodeType, Node.ELEMENT_NODE);

        done();
      });
    });
  });
});
