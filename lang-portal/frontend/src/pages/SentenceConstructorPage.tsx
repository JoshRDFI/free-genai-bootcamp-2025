import React from 'react';
import { SentenceConstructor } from '../components/SentenceConstructor';

export const SentenceConstructorPage: React.FC = () => {
    return (
        <div className="min-h-screen bg-gray-50">
            <div className="container mx-auto py-8">
                <h1 className="text-3xl font-bold text-center mb-8">
                    Sentence Constructor
                </h1>
                <SentenceConstructor />
            </div>
        </div>
    );
}; 