const e = React.createElement;

const AppPlaceholder = () => (
    <p>
        This page is under construction! For now, check out what else I'm building at <a class="inline" href="https://tarpey.dev">tarpey.dev</a>.
    </p>
);

class Home extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div>
                <AppPlaceholder />
            </div>
        );
    }
}

const domContainer = document.querySelector('#root');
ReactDOM.render(e(Home), domContainer);
