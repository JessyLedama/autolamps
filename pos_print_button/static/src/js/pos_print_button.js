openerp.pos_print_button = function (instance, local) {
    module = instance.point_of_sale;
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    var round_pr = instance.web.round_precision;
    module.RequisitionScreenWidget = module.ScreenWidget.extend({
        template: 'RequisitionScreenWidget',

        show_numpad: false,
        show_leftpane: false,

        show: function () {
            this._super();
            var self = this;

            var print_button = this.add_action_button({
                label: _t('Print'),
                icon: '/point_of_sale/static/src/img/icons/png48/printer.png',
                click: function () { self.print(); },
            });

            var finish_button = this.add_action_button({
                label: _t('Next Order'),
                icon: '/point_of_sale/static/src/img/icons/png48/go-next.png',
                click: function () { self.finishOrder(); },
            });

            this.refresh();

            if (!this.pos.get('selectedOrder')._printed) {
                this.print();
            }

            //
            // The problem is that in chrome the print() is asynchronous and doesn't
            // execute until all rpc are finished. So it conflicts with the rpc used
            // to send the orders to the backend, and the user is able to go to the next 
            // screen before the printing dialog is opened. The problem is that what's 
            // printed is whatever is in the page when the dialog is opened and not when it's called,
            // and so you end up printing the product list instead of the receipt... 
            //
            // Fixing this would need a re-architecturing
            // of the code to postpone sending of orders after printing.
            //
            // But since the print dialog also blocks the other asynchronous calls, the
            // button enabling in the setTimeout() is blocked until the printing dialog is 
            // closed. But the timeout has to be big enough or else it doesn't work
            // 2 seconds is the same as the default timeout for sending orders and so the dialog
            // should have appeared before the timeout... so yeah that's not ultra reliable. 

            finish_button.set_disabled(true);
            setTimeout(function () {
                finish_button.set_disabled(false);
            }, 2000);
        },
        print: function () {
            this.pos.get('selectedOrder')._printed = true;
            window.print();
        },
        finishOrder: function () {
            this.pos.get('selectedOrder').destroy();
        },
        refresh: function () {
            var order = this.pos.get('selectedOrder');
            var orderLines = order.get('orderLines').models;
            var _locationDict = order.pos.config.stock_locations;
            var locations = JSON.parse(_locationDict)
            $('.pos-receipt-container', this.$el).html(QWeb.render('RequisitionTicket', {
                widget: this,
                order: order,
                locations: locations,
                orderlines: orderLines,
                paymentlines: order.get('paymentLines').models,
            }));
        },
        close: function () {
            this._super();
        }
    });

    module.PrintButtonWidget = module.PosBaseWidget.extend({
        template: 'PrintButtonWidget',
        
        renderElement: function () {
            var self = this;
            this._super();
            this.$el.click(function () {
                if (!confirm(_t("Do you want to print order before confirming?"))) {
                    return false;
                }
                // Do your printing here
                var ss = self.pos.pos_widget.screen_selector;
                ss.set_current_screen('requisition');
            });
        },

        refresh_receipt: function () {
            var order = this.pos.get('selectedOrder');
            var orderLines = order.get('orderLines').models;

            $('.pos-receipt-container', this.$el).html(QWeb.render('PosTicket', {
                widget: this,
                order: order,
                orderlines: order.get('orderLines').models,
                paymentlines: []
            }));

        },

        print_receipt: function () {
            self.pos_widget.screen_selector.set_current_screen('requisition');
            this.refresh_receipt()
            //console.log(this.pos.get('selectedOrder'))
            // setTimeout(function () {
            //     window.print();
            // }, 2000)
        },
    });

    module.PosWidget = module.PosWidget.extend({
        build_widgets: function () {
            this._super();
            // Add buttons
            this.print_button = new module.PrintButtonWidget(this, {});

            this.requisition_screen = new module.RequisitionScreenWidget(this, {});
            this.requisition_screen.appendTo(this.$('.screens'));

            this.screen_selector.screen_set['requisition'] = this.requisition_screen;
            this.requisition_screen.hide();


        },
    });

    module.OrderWidget = module.OrderWidget.extend({
        renderElement: function (scrollbottom) {
            this._super(scrollbottom);
            // Only show button when there are order-lines
            if (this.pos_widget.print_button && (this.pos.get('selectedOrder').get('orderLines').length > 0)) {
                this.pos_widget.print_button.appendTo(
                    this.pos_widget.$('div.summary')
                );
            }
        }
    });

};