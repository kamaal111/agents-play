import { Toaster, type DefaultToastOptions } from 'react-hot-toast';

const toastOptions: DefaultToastOptions = {
  error: { duration: 3000, style: { background: '#DD2712', color: '#ffffff' } },
};

function ThemeProvider(props: React.PropsWithChildren) {
  return (
    <>
      {props.children}
      <Toaster toastOptions={toastOptions} />
    </>
  );
}

export default ThemeProvider;
