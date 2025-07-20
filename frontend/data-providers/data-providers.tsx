import type React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import ThemeProvider from './theme-provider';

const queryClient = new QueryClient();

function DataProviders(props: React.PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>{props.children}</ThemeProvider>
    </QueryClientProvider>
  );
}

export default DataProviders;
