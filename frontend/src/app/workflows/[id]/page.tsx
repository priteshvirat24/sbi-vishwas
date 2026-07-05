import WorkflowClient from './WorkflowClient';

export function generateStaticParams() {
  return [{ id: 'demo' }];
}

export default function Page() {
  return <WorkflowClient />;
}
