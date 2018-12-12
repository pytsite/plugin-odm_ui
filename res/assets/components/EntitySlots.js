import './EntitySlots.scss';
import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import setupWidget from '@pytsite/widget';
import {Slots, TwoButtonsModal, Select2} from '@pytsite/widget/components';
import {lang} from '@pytsite/assetman';
import httpApi from '@pytsite/http-api';
import odmHttpApi from '@pytsite/odm-http-api';

export default class EntitySlots extends React.Component {
    static propTypes = {
        emptySlotTitle: PropTypes.string,
        emptySlotRenderer: PropTypes.func,
        enabled: PropTypes.bool,
        entityTitleField: PropTypes.string.isRequired,
        entityUrlField: PropTypes.string,
        entityThumbField: PropTypes.string,
        maxSlots: PropTypes.number,
        modalTitle: PropTypes.string,
        model: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        searchBy: PropTypes.string,
        searchDelay: PropTypes.number,
        searchMinimumInputLength: PropTypes.number,
        slotRenderer: PropTypes.func,
        sortBy: PropTypes.string,
        sortOrder: PropTypes.number,
        value: PropTypes.arrayOf(PropTypes.string)
    };

    static defaultProps = {
        entityTitleField: 'title',
        entityThumbField: 'thumbnail',
        entityUrlField: 'url',
        maxSlots: 1000,
        searchDelay: 250,
        searchMinimumInputLength: 1,
        sortOrder: 1,
    };

    constructor(props) {
        super(props);

        this.state = {
            entities: {},
            isModalOpened: false,
            selectedEntityRef: null,
        };

        this.emptySlotRenderer = this.emptySlotRenderer.bind(this);
        this.slotRenderer = this.slotRenderer.bind(this);
        this.onModalToggle = this.onModalToggle.bind(this);
        this.onModalClickOk = this.onModalClickOk.bind(this);
        this.onSlotBtnDeleteClick = this.onSlotBtnDeleteClick.bind(this);
    }

    componentDidMount() {
        const urlArgs = {
            refs: JSON.stringify(this.props.value),
            sort_by: this.props.sortBy,
            sort_order: this.props.sortOrder,
        };

        odmHttpApi.getAllEntities(this.props.model, urlArgs).then(data => {
            const entities = {};

            data.map(entity => entities[entity.ref] = entity);

            this.setState({
                entities: entities,
            });
        });
    }

    onModalToggle() {
        this.setState({isModalOpened: !this.state.isModalOpened});
    }

    onModalClickOk() {
        if (!this.state.selectedEntityRef)
            return;

        httpApi.get(`odm/entity/${this.state.selectedEntityRef}`).then(entity => {
            const entities = this.state.entities;
            entities[entity.ref] = entity;
            this.setState({entities: entities})
        });

        this.setState({selectedEntityRef: null});
    }

    onSlotBtnDeleteClick(entityRef) {
        if (confirm(lang.t('odm_ui@confirm_delete'))) {
            const entities = this.state.entities;
            delete entities[entityRef];
            this.setState({entities: entities});
        }
    }

    emptySlotRenderer() {
        return <i className={'fa fas fa-plus fa-2x'}></i>
    }

    slotRenderer(entity) {
        const title = <div className="entity-title">
            {entity[this.props.entityTitleField]}
        </div>;

        let thumb = null;
        if (entity.hasOwnProperty(this.props.entityThumbField)) {
            thumb = <img className={'entity-thumbnail'}
                         src={entity[this.props.entityThumbField]}
                         alt={entity[this.props.entityTitleField]}
            />;

        }

        let actions = null;
        if (this.props.enabled) {
            actions = <div className={'entity-actions'}>
                <button className={'btn btn-sm btn-danger'} onClick={e => {
                    e.preventDefault();
                    this.onSlotBtnDeleteClick(entity.ref);
                }}>
                    <i className={'fa fas fa-times fa-remove'}></i>
                </button>
            </div>
        }

        return <React.Fragment>
            <input type={'hidden'} name={`${this.props.name}[]`} value={entity.ref}/>
            {actions}
            {thumb}
            {title}
        </React.Fragment>
    }

    render() {
        const selectOpts = {
            ajax: {
                url: httpApi.url(`odm/entities/${this.props.model}`, {
                    sort_by: this.props.sortBy,
                    sort_order: this.props.sortOrder,
                    exclude: JSON.stringify(Object.keys(this.state.entities)),
                }),
                data: params => ({
                    search_by: this.props.searchBy,
                    search: params.term,
                }),
                processResults: d => ({
                    results: d.map(e => ({
                        id: e.ref,
                        text: e.title,
                    }))
                }),
                delay: this.props.searchDelay,
            },
            minimumInputLength: this.props.searchMinimumInputLength,
        };

        return <React.Fragment>
            <input type={'hidden'} name={`${this.props.name}[]`} value={''}/>

            <TwoButtonsModal isOpen={this.state.isModalOpened}
                             title={this.props.modalTitle}
                             onToggle={this.onModalToggle}
                             onClickCancel={() => this.setState({selectedEntityRef: null})}
                             onClickOk={this.onModalClickOk}
                             isOkButtonDisabled={!this.state.selectedEntityRef}

            >
                <Select2 options={selectOpts}
                         onSelect={event => this.setState({selectedEntityRef: event.target.value})}
                />
            </TwoButtonsModal>

            <Slots data={this.state.entities}
                   emptySlotTitle={this.props.emptySlotTitle}
                   emptySlotRenderer={this.props.emptySlotRenderer || this.emptySlotRenderer}
                   enabled={this.props.enabled}
                   onEmptySlotClick={this.onModalToggle}
                   slotRenderer={this.props.slotRenderer || this.slotRenderer}
            />
        </React.Fragment>


    }
}

setupWidget('plugins.odm_ui._widget.EntitySlots', widget => {
    const c = <EntitySlots emptySlotTitle={widget.data('emptySlotTitle')}
                           enabled={widget.data('enabled') === 'True'}
                           entityTitleField={widget.data('entityTitleField')}
                           entityThumbField={widget.data('entityThumbField')}
                           entityUrlField={widget.data('entityUrlField')}
                           maxSlots={widget.data('maxSlots')}
                           modalTitle={widget.data('modalTitle')}
                           model={widget.data('model')}
                           name={widget.uid}
                           sortBy={widget.data('sortBy')}
                           sortOrder={widget.data('sortOrder')}
                           searchBy={widget.data('searchBy')}
                           searchDelay={widget.data('searchDelay')}
                           searchMinimumInputLength={widget.data('searchMinimumInputLength')}
                           value={widget.data('value')}

    />;

    ReactDOM.render(c, widget.find('.widget-component')[0]);
});
