function pos_autolamps_models(instance, module){
    module = instance.point_of_sale;
    var Model = instance.web.Model;

    var _super = module.Order;
    module.Order = module.Order.extend({
        initialize: function (attributes) {
            _super.prototype.initialize.call(this, attributes);
            // Do the sequence in a deferred get function()
            return this.get_sequences();

        },

        get_sequences: function () {
            var self = this;
            var sequence = this.uid;
            var _orderId = this.pos.config.last_order_id;
            if (this.pos.config.custom_sequence_id) {
                var defer = $.Deferred();
                new Model('pos.order')
                    .call('get_order_sequence', [_orderId])
                    .then(function (value) {
                        self.set('name', value[0]['sequence']);
                        defer.resolve();
                    });
                return defer;
            }
            return sequence;

        },

    });

};
